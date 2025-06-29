module mux4 (
    input [1:0] sel,
    input [3:0] data,
    output out
);
    assign out = data[sel];
endmodule

module testbench;
    reg [3:0] data;
    reg [1:0] sel;
    wire out;

    mux4 uut(sel, data, out);

    initial begin
        $dumpfile("mux4.vcd");
        $dumpvars(0, uut);

        data = 4'b1010;
        sel = 2'b00; #10;
        sel = 2'b01; #10;
        sel = 2'b10; #10;
        sel = 2'b11; #10;
        $finish;
    end
endmodule


// ---- Auto-generated testbench ----
`timescale 1ns/1ps
module testbench_tb;
    // Declare regs for inputs and wires for outputs

    // Instantiate the DUT
    testbench uut (
    );

    // Input stimulus
    initial begin
        #10;
        integer i;
        for (i = 0; i < 16; i = i+1) begin
            #10;
        end
        $finish;
    end

endmodule